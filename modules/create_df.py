import pandas as pd
import re

def pre_treat(review_pages: list):
    '''
    # i - página
    # j - review
    # k - elemento da review
    # reviews[i][j][k]
    '''
    treated = []
    for page in review_pages:
        reviews = []
        for review in page:
            review_info = []

            for k in range(len(review)):
                element = review[k]
                if element.find('\n') != -1:
                    review_info.append(element)
                    review_info.append(review[-1])
                    break
                review_info.append(element)

            reviews.append(review_info)    
        treated.append(reviews)
    return treated

def create_df(review_pages:list, PRODUCT_ID):
    '''
    Returns a Pandas DF.
    Inputs: 
        review_pages - pages list of unformatted reviews list
        hasDiffModels - boolean that indicates if the reviews have different models
    '''

    df_columns = ['username', 'title', 'model', 'verified', 'date', 'region', 'text', 'stars', 'id']
    
    df = pd.DataFrame(columns=df_columns)

    reviews = []
    for page in review_pages:
        for review in page:
            reviews.append(review)
    

    for i, review in enumerate(reviews):
        #print(review)
        username = review[0]
        stars = review[1]
        title = review[2]
        date_region = review[3]
        
        if review[4] == 'Verified Purchase':
            verified = review[4]
        else:
            verified = ''
            text = review[4]
        
        if review[-1].find('\n') != -1:
            text = review[-1]
            model = ''
        else:
            text = review[-2]
            model = review[-1]
        
        if review[5].find('\n') != -1:
            text = review[5]
            
        # econtra uma sequencia de números
        #ATS: deveria usar regex
        stars = stars.split(' ')[0]

        # encontra a data que está após a palavra 'on'
        pattern = r'\bon\b\s+(.+)'
        date = re.findall(pattern, date_region)

        # encontra a região após 'in the' e antes de 'on'
        pattern = r'\bin the\b\s+(.+)\s+\bon\b'
        region = re.findall(pattern, date_region)

        df.loc[i] = [username, title, model, verified, date[0], region[0], text, stars, PRODUCT_ID]


    return df